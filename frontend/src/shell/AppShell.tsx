import type { ReactNode } from "react";
import { Link } from "react-router";

import styles from "./AppShell.module.css";
import { GearIcon } from "./GearIcon";
import { ThemeSwitch } from "./ThemeSwitch";

/** The frame of every page: the brass header with the brand and the theme switch. */
export function AppShell({ children }: { children: ReactNode }) {
  return (
    <>
      <header className={styles.header}>
        <Link to="/" className={styles.brand}>
          <GearIcon />
          <span className={styles.brandName}>Chronicler</span>
        </Link>
        <ThemeSwitch />
      </header>
      {children}
    </>
  );
}
