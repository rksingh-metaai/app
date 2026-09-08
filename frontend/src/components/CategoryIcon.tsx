import React from "react";
import {
  ForkKnife,
  ShoppingBag,
  Car,
  Receipt,
  FilmSlate,
  Heartbeat,
  Money,
  TrendUp,
  ShoppingCart,
  DotsThreeCircle,
  IconProps,
} from "phosphor-react-native";

const MAP: Record<string, React.ComponentType<IconProps>> = {
  food: ForkKnife,
  shopping: ShoppingBag,
  transport: Car,
  bills: Receipt,
  entertainment: FilmSlate,
  health: Heartbeat,
  salary: Money,
  investment: TrendUp,
  groceries: ShoppingCart,
  other: DotsThreeCircle,
};

export function CategoryIcon({
  category,
  size = 22,
  color,
  weight = "fill",
}: {
  category: string;
  size?: number;
  color: string;
  weight?: IconProps["weight"];
}) {
  const Comp = MAP[category] ?? DotsThreeCircle;
  return <Comp size={size} color={color} weight={weight} />;
}
