const DEFAULT_ICE_SERVERS = [
  { urls: 'stun:stun.l.google.com:19302' },
  { urls: 'stun:stun1.l.google.com:19302' },
];

const noop = () => {};

class EventEmitter {
  constructor() {
    this.listeners = new Map();
  }

  on(event, handler) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event).add(handler);
    return () => this.off(event, handler);
  }

  off(event, handler) {
    this.listeners.get(event)?.delete(handler);
  }

  emit(event, payload) {
    this.listeners.get(event)?.forEach((handler) => {
      try {
        handler(payload);
      } catch (error) {
        console.error('[CallClient] event handler failed', error);
      }
    });
  }
}

async function resolveAuthToken() {
  if (typeof window.getAuthToken === 'function') {
    const token = await window.getAuthToken();
    if (token) {
      return token;
    }
  }
  try {
    return localStorage.getItem('auth_token') || '';
  } catch (error) {
    console.warn('[CallClient] Unable to read auth token', error);
    return '';
  }
}

function resolveCsrfToken() {
  const element = document.querySelector('[name=csrfmiddlewaretoken]');
  return element ? element.value : '';
}

function buildUrl(base, path = '') {
  if (!base) return path;
  const trimmedBase = base.replace(/\/+$/, '');
  const trimmedPath = String(path || '').replace(/^\/+/, '');
  return trimmedPath ? `${trimmedBase}/${trimmedPath}` : trimmedBase;
}

export default function initialiseCallClient(globalConfig = {}) {
  return new CallClient(globalConfig);
}

class CallClient {
  constructor(config = {}) {
    this.config = config;
    this.iceServers = config.iceServers || DEFAULT_ICE_SERVERS;
    this.apiBaseUrl = config.apiBaseUrl || (window.API_BASE_URL ?? '/api');
    this.wsBaseUrl = config.wsBaseUrl || (window.WS_BASE_URL ?? '');
    this.eventBus = new EventEmitter();
    this.peerConnections = new Map();
    this.remoteStreams = new Map();
    this.localStream = null;
    this.socket = null;
    this.socketReady = null;
    this.roomId = null;
    this.callType = 'audio';
  }

  on(event, handler) {
    return this.eventBus.on(event, handler);
  }

  async startCall({ roomId, callType = 'audio', participants = [] } = {}) {
    this.roomId = roomId;
    this.callType = callType;
    await this._ensureLocalStream(callType);
    await this._ensureSocket();

    // إنشاء جلسة عبر REST
    const token = await resolveAuthToken();
    const payload = {
      room: roomId,
      call_type: callType,
      participants,
    };
    await this._apiFetch('calls/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Token ${token}` : undefined,
        'X-CSRFToken': resolveCsrfToken(),
      },
      body: JSON.stringify(payload),
    });

    // دعوة المشاركين عبر WebSocket
    if (participants.length > 0) {
      this._sendSignal('invite', { participants });
    }

    this.eventBus.emit('local-stream', this.localStream);
  }

  async answerCall({ roomId, callType = 'audio' } = {}) {
    this.roomId = roomId;
    this.callType = callType;
    await this._ensureLocalStream(callType);
    await this._ensureSocket();
    this.eventBus.emit('local-stream', this.localStream);
  }

  async endCall(reason = 'normal') {
    this._sendSignal('end', { reason });
    try {
      await this._apiFetch(`calls/${this.roomId}/end/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': await resolveAuthToken().then((token) => token ? `Token ${token}` : undefined),
          'X-CSRFToken': resolveCsrfToken(),
        },
        body: JSON.stringify({ reason }),
      });
    } catch (error) {
      console.warn('[CallClient] Failed to end call via API', error);
    }
    this._dispose();
  }

  async _ensureLocalStream(callType) {
    if (this.localStream) {
      return this.localStream;
    }
    const constraints = callType === 'video'
      ? { audio: true, video: { facingMode: 'user' } }
      : { audio: true, video: false };
    try {
      this.localStream = await navigator.mediaDevices.getUserMedia(constraints);
      return this.localStream;
    } catch (error) {
      console.error('[CallClient] getUserMedia failed', error);
      throw error;
    }
  }

  async _ensureSocket() {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      return this.socket;
    }
    if (this.socketReady) {
      return this.socketReady;
    }

    this.socketReady = new Promise(async (resolve, reject) => {
      try {
        const token = await resolveAuthToken();
        const base = this.wsBaseUrl || `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`;
        const url = buildUrl(base, `ws/call/${this.callType}/${this.roomId}/`);
        const socketUrl = token ? `${url}?token=${encodeURIComponent(token)}` : url;
        this.socket = new WebSocket(socketUrl);
        this.socket.onopen = () => resolve(this.socket);
        this.socket.onerror = (error) => {
          console.error('[CallClient] WebSocket error', error);
          reject(error);
        };
        this.socket.onclose = () => this._disposeSocket();
        this.socket.onmessage = (event) => this._handleSocketMessage(event);
      } catch (error) {
        reject(error);
      }
    });

    return this.socketReady;
  }

  _disposeSocket() {
    this.socketReady = null;
    this.socket = null;
  }

  _sendSignal(action, data = {}, metadata = {}) {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      return;
    }
    const message = {
      action,
      data,
      metadata,
    };
    this.socket.send(JSON.stringify(message));
  }

  async _handleSocketMessage(event) {
    let payload = null;
    try {
      payload = JSON.parse(event.data);
    } catch (error) {
      console.warn('[CallClient] Invalid signal payload', event.data);
      return;
    }

    const currentUserId = this.config.currentUserId || window.__APP_CONFIG__?.userId || null;
    const { from, action, data, metadata = {} } = payload;
    if (!from || from === currentUserId) {
      return; // تجاهل الرسائل الذاتية
    }

    const target = metadata.target;
    if (target && currentUserId && Number(target) !== Number(currentUserId)) {
      return;
    }

    switch (action) {
      case 'offer':
        await this._handleOffer(from, data);
        break;
      case 'answer':
        await this._handleAnswer(from, data);
        break;
      case 'ice':
        await this._handleIceCandidate(from, data);
        break;
      case 'invite-sent':
        this.eventBus.emit('invite-sent', data);
        break;
      case 'ended':
        this.eventBus.emit('call-ended', data);
        this._dispose();
        break;
      case 'joined':
      case 'left':
        this.eventBus.emit(`participant-${action}`, payload);
        break;
      default:
        this.eventBus.emit('signal', payload);
    }
  }

  async _handleOffer(remoteUserId, data = {}) {
    const description = data?.description;
    if (!description) return;
    const pc = await this._ensurePeerConnection(remoteUserId);
    await pc.setRemoteDescription(description);
    const answer = await pc.createAnswer();
    await pc.setLocalDescription(answer);
    this._sendSignal('answer', { description: pc.localDescription }, { target: remoteUserId });
  }

  async _handleAnswer(remoteUserId, data = {}) {
    const description = data?.description;
    if (!description) return;
    const pc = await this._ensurePeerConnection(remoteUserId);
    await pc.setRemoteDescription(description);
  }

  async _handleIceCandidate(remoteUserId, data = {}) {
    const candidate = data?.candidate;
    if (!candidate) return;
    const pc = await this._ensurePeerConnection(remoteUserId);
    try {
      await pc.addIceCandidate(candidate);
    } catch (error) {
      console.error('[CallClient] Failed to add ICE candidate', error);
    }
  }

  async initiatePeer(remoteUserId) {
    const pc = await this._ensurePeerConnection(remoteUserId, true);
    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
    this._sendSignal('offer', { description: pc.localDescription }, { target: remoteUserId });
  }

  async _ensurePeerConnection(remoteUserId, createOffer = false) {
    if (this.peerConnections.has(remoteUserId)) {
      return this.peerConnections.get(remoteUserId);
    }

    const pc = new RTCPeerConnection({ iceServers: this.iceServers });
    this.peerConnections.set(remoteUserId, pc);

    const localStream = await this._ensureLocalStream(this.callType);
    localStream.getTracks().forEach((track) => pc.addTrack(track, localStream));

    pc.onicecandidate = ({ candidate }) => {
      if (candidate) {
        this._sendSignal('ice', { candidate }, { target: remoteUserId });
      }
    };

    pc.ontrack = (event) => {
      const stream = event.streams[0];
      if (stream) {
        this.remoteStreams.set(remoteUserId, stream);
        this.eventBus.emit('remote-stream', { userId: remoteUserId, stream });
      }
    };

    pc.onconnectionstatechange = () => {
      this.eventBus.emit('peer-state', {
        userId: remoteUserId,
        state: pc.connectionState,
      });
      if (['disconnected', 'failed', 'closed'].includes(pc.connectionState)) {
        this.remoteStreams.delete(remoteUserId);
        this.peerConnections.delete(remoteUserId);
      }
    };

    if (createOffer) {
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);
      this._sendSignal('offer', { description: pc.localDescription }, { target: remoteUserId });
    }

    return pc;
  }

  async _apiFetch(path, options = {}) {
    const url = buildUrl(this.apiBaseUrl, path);
    const headers = {
      Accept: 'application/json',
      ...(options.headers || {}),
    };
    const finalOptions = { ...options, headers };
    const response = await fetch(url, finalOptions);
    if (!response.ok) {
      const error = await response.text().catch(() => '');
      throw new Error(error || `API call failed (${response.status})`);
    }
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      return response.json().catch(() => ({}));
    }
    return {};
  }

  _dispose() {
    this.peerConnections.forEach((pc) => {
      try {
        pc.close();
      } catch (error) {
        noop(error);
      }
    });
    this.peerConnections.clear();
    this.remoteStreams.clear();

    if (this.localStream) {
      this.localStream.getTracks().forEach((track) => track.stop());
      this.localStream = null;
    }

    if (this.socket) {
      try {
        this.socket.close();
      } catch (error) {
        noop(error);
      }
      this.socket = null;
    }
    this.socketReady = null;
  }
}

