'use client';

import CountUp from 'react-countup';

interface AnimatedNumberProps {
  value: number;
  suffix?: string;
  prefix?: string;
  decimals?: number;
  duration?: number;
  className?: string;
}

export function AnimatedNumber({
  value,
  suffix = '',
  prefix = '',
  decimals = 0,
  duration = 1.5,
  className,
}: AnimatedNumberProps) {
  return (
    <CountUp
      start={0}
      end={value}
      duration={duration}
      decimals={decimals}
      suffix={suffix}
      prefix={prefix}
      className={className}
    />
  );
}
