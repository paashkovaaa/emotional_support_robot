import { useEffect, useState } from 'react';

interface EmiAvatarProps {
  size?: number;
  state?: 'idle' | 'typing' | 'happy';
  className?: string;
}

export default function EmiAvatar({ size = 40, state = 'idle', className = '' }: EmiAvatarProps) {
  const [blink, setBlink] = useState(false);

  // Random blinking
  useEffect(() => {
    if (state === 'typing') return;
    const schedule = () => {
      const delay = 2500 + Math.random() * 3000;
      return setTimeout(() => {
        setBlink(true);
        setTimeout(() => {
          setBlink(false);
          scheduleRef.current = schedule();
        }, 150);
      }, delay);
    };
    const scheduleRef = { current: schedule() };
    return () => clearTimeout(scheduleRef.current);
  }, [state]);

  const isTyping = state === 'typing';
  const isHappy = state === 'happy';

  return (
    <div
      className={`relative inline-flex items-center justify-center ${className}`}
      style={{ width: size, height: size }}
    >
      <svg
        width={size}
        height={size}
        viewBox="0 0 80 80"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={isTyping ? 'animate-pulse' : 'animate-[float_3s_ease-in-out_infinite]'}
        style={{ display: 'block' }}
      >
        {/* Antenna base */}
        <rect x="37" y="6" width="6" height="10" rx="3" fill="#a78bfa" />
        {/* Antenna ball */}
        <circle
          cx="40"
          cy="5"
          r="5"
          fill={isTyping ? '#f472b6' : '#c4b5fd'}
          className={isTyping ? 'animate-ping' : ''}
          style={isTyping ? { transformOrigin: '40px 5px' } : {}}
        />
        {/* Antenna ball inner (stays visible during ping) */}
        {isTyping && <circle cx="40" cy="5" r="5" fill="#f472b6" />}

        {/* Head */}
        <rect x="12" y="16" width="56" height="44" rx="16" fill="#c4b5fd" />
        {/* Head shine */}
        <ellipse cx="28" cy="24" rx="8" ry="5" fill="white" opacity="0.5" />

        {/* Left eye */}
        <ellipse
          cx="27"
          cy="36"
          rx="7"
          ry={blink ? 1 : isTyping ? 7 : 7}
          fill="white"
          className="transition-all duration-75"
        />
        <circle
          cx="27"
          cy="36"
          r={blink ? 0 : 4}
          fill={isTyping ? '#f472b6' : '#7c3aed'}
          className="transition-all duration-75"
        />
        {/* Left pupil shine */}
        {!blink && <circle cx="29" cy="34" r="1.5" fill="white" opacity="0.8" />}

        {/* Right eye */}
        <ellipse
          cx="53"
          cy="36"
          rx="7"
          ry={blink ? 1 : isTyping ? 7 : 7}
          fill="white"
          className="transition-all duration-75"
        />
        <circle
          cx="53"
          cy="36"
          r={blink ? 0 : 4}
          fill={isTyping ? '#f472b6' : '#7c3aed'}
          className="transition-all duration-75"
        />
        {/* Right pupil shine */}
        {!blink && <circle cx="55" cy="34" r="1.5" fill="white" opacity="0.8" />}

        {/* Mouth */}
        {isHappy || isTyping ? (
          /* Smile */
          <path
            d="M30 52 Q40 60 50 52"
            stroke={isTyping ? '#f472b6' : '#7c3aed'}
            strokeWidth="3"
            strokeLinecap="round"
            fill="none"
          />
        ) : (
          /* Neutral gentle smile */
          <path
            d="M32 52 Q40 57 48 52"
            stroke="#a78bfa"
            strokeWidth="2.5"
            strokeLinecap="round"
            fill="none"
          />
        )}

        {/* Cheek blush left */}
        <ellipse cx="18" cy="44" rx="5" ry="3" fill="#fda4af" opacity="0.5" />
        {/* Cheek blush right */}
        <ellipse cx="62" cy="44" rx="5" ry="3" fill="#fda4af" opacity="0.5" />

        {/* Body (small) */}
        <rect x="28" y="58" width="24" height="14" rx="8" fill="#c4b5fd" />
        {/* Body detail */}
        <rect x="34" y="63" width="12" height="3" rx="1.5" fill="#7c3aed" opacity="0.4" />
      </svg>

      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-4px); }
        }
      `}</style>
    </div>
  );
}

