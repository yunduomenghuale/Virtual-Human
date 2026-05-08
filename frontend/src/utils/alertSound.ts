/**
 * 播放消防车高风险警报声（Web Audio API）。
 * 消防车声特征：高低频率交替（800Hz ↔ 1200Hz），锯齿波更刺耳，持续约 3 秒。
 */
export function playFireTruckAlert() {
  try {
    const AudioCtx = (window as any).AudioContext || (window as any).webkitAudioContext
    if (!AudioCtx) return
    const ctx = new AudioCtx()

    // 消防车声参数
    const lowFreq = 750
    const highFreq = 1250
    const halfPeriod = 0.45  // 半个周期时长（从低到高或从高到低）
    const cycles = 3         // 循环次数
    const duration = halfPeriod * 2 * cycles

    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.connect(gain)
    gain.connect(ctx.destination)

    // 锯齿波更像警报
    osc.type = 'sawtooth'

    // 初始音量较大，然后慢慢衰减（避免刺耳到无法承受）
    gain.gain.setValueAtTime(0.7, ctx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.3, ctx.currentTime + duration * 0.8)

    // 频率交替：低 → 高 → 低 → 高 → 低 → 高
    let t = ctx.currentTime
    for (let i = 0; i < cycles; i++) {
      osc.frequency.setValueAtTime(lowFreq, t)
      osc.frequency.setValueAtTime(highFreq, t + halfPeriod)
      t += halfPeriod * 2
    }
    osc.frequency.setValueAtTime(lowFreq, t)

    osc.start(ctx.currentTime)
    osc.stop(ctx.currentTime + duration + 0.1)

    // 结束后清理
    setTimeout(() => {
      try { ctx.close() } catch { /* noop */ }
    }, (duration + 0.2) * 1000)
  } catch { /* 浏览器限制时静默 */ }
}
