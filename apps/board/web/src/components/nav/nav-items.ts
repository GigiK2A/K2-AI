import { LayoutDashboard, Users, FileCheck, ListTodo, Wallet, Calendar, Brain, Bot } from "lucide-react";
import type { LucideIcon } from "lucide-react";

export interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
}

export const navItems: NavItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/pipeline", label: "Pipeline", icon: Users },
  { href: "/approvazioni", label: "Approvazioni", icon: FileCheck },
  { href: "/tasks", label: "Tasks", icon: ListTodo },
  { href: "/revenue", label: "Revenue", icon: Wallet },
  { href: "/calendario", label: "Calendario", icon: Calendar },
  { href: "/memos", label: "Memos", icon: Brain },
  { href: "/k-bot", label: "K-BOT", icon: Bot },
];

export const primaryMobileItems = navItems.slice(0, 4);
export const overflowMobileItems = navItems.slice(4);
