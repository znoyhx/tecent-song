import type { ReactNode } from 'react';

type GameShellProps = {
  main: ReactNode;
  side: ReactNode;
};

export function GameShell({ main, side }: GameShellProps) {
  return (
    <div className="game-shell">
      <main className="game-main">{main}</main>
      <aside className="game-side">{side}</aside>
    </div>
  );
}
