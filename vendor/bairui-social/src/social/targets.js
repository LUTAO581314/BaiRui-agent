export function parseSocialTarget(targetId = '') {
  const raw = String(targetId || '').trim()
  if (raw.startsWith('discord:')) {
    const [, channelId, userId = ''] = raw.split(':')
    return channelId ? { platform: 'discord', channelId, userId, raw } : null
  }
  if (raw.startsWith('feishu:')) {
    const [, receiveIdType, ...rest] = raw.split(':')
    const receiveId = rest.join(':')
    return receiveIdType && receiveId ? { platform: 'feishu', receiveIdType, receiveId, raw } : null
  }
  if (raw.startsWith('wechat:official:')) {
    return { platform: 'wechat-official', openId: raw.slice('wechat:official:'.length), raw }
  }
  if (raw.startsWith('wecom:webhook:')) {
    return { platform: 'wecom-webhook', key: raw.slice('wecom:webhook:'.length), raw }
  }
  if (raw.startsWith('wechat:clawbot:')) {
    return { platform: 'wechat-clawbot', userId: raw.slice('wechat:clawbot:'.length), raw }
  }
  if (raw.startsWith('qq:napcat:private:')) {
    return { platform: 'qq-napcat', messageType: 'private', userId: raw.slice('qq:napcat:private:'.length), raw }
  }
  if (raw.startsWith('qq:napcat:group:')) {
    return { platform: 'qq-napcat', messageType: 'group', groupId: raw.slice('qq:napcat:group:'.length), raw }
  }
  if (raw.startsWith('qq:napcat:')) {
    return { platform: 'qq-napcat', messageType: 'private', userId: raw.slice('qq:napcat:'.length), raw }
  }
  return null
}

