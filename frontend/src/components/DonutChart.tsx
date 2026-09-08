import React from "react";
import { View } from "react-native";
import Svg, { Circle } from "react-native-svg";

type Segment = { amount: number; color: string };

export function DonutChart({
  segments,
  size = 160,
  strokeWidth = 22,
  trackColor,
}: {
  segments: Segment[];
  size?: number;
  strokeWidth?: number;
  trackColor: string;
}) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const total = segments.reduce((s, seg) => s + seg.amount, 0) || 1;

  let offsetAcc = 0;
  const arcs = segments.map((seg, i) => {
    const fraction = seg.amount / total;
    const dash = fraction * circumference;
    const gap = circumference - dash;
    const rotation = (offsetAcc / total) * 360 - 90;
    offsetAcc += seg.amount;
    return (
      <Circle
        key={i}
        cx={size / 2}
        cy={size / 2}
        r={radius}
        stroke={seg.color}
        strokeWidth={strokeWidth}
        strokeDasharray={`${dash} ${gap}`}
        strokeLinecap="butt"
        fill="none"
        transform={`rotate(${rotation} ${size / 2} ${size / 2})`}
      />
    );
  });

  return (
    <View style={{ width: size, height: size }}>
      <Svg width={size} height={size}>
        <Circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={trackColor}
          strokeWidth={strokeWidth}
          fill="none"
        />
        {arcs}
      </Svg>
    </View>
  );
}
