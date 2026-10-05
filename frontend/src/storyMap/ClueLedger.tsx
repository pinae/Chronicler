import type { BeatSummary, KnowledgeMap, RiverColumn, RiverThread } from "../api/types";
import styles from "./ClueLedger.module.css";
import { cluesTo, payoffAt, preparation } from "./clues";
import { howKnown } from "./knowledgeLayout";
import { threadLabel } from "./threadLabel";

type Props = { beats: BeatSummary[]; column: RiverColumn; thread: RiverThread; knowledgeMap: KnowledgeMap };

/** The Three Clue Rule as a table: the beats that filled the reading's steps against the players, and
 * how many clues each player had before the payoff. */
export function ClueLedger({ beats, column, thread, knowledgeMap }: Props) {
  const clues = cluesTo(column, thread);
  const payoff = payoffAt(clues);
  const players = knowledgeMap.columns.map((player) => ({
    id: player.player,
    name: player.name,
    known: new Map(player.known.map((cell) => [cell.t, cell])),
  }));
  return (
    <table aria-label={`Clues to ${threadLabel(thread)}`}>
      <thead>
        <tr>
          <th scope="col">t</th>
          <th scope="col">Beat</th>
          <th scope="col">Step</th>
          {players.map((player) => (
            <th key={player.id} scope="col">
              {player.name}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {clues.map((clue) => (
          <tr key={clue.t}>
            <td>{clue.t}</td>
            <td>{beats.find((beat) => beat.t === clue.t)?.text}</td>
            <td>{`${clue.steps.join(", ")}${clue.payoff ? " (payoff)" : ""}`}</td>
            {players.map((player) => (
              <td key={player.id}>{howKnown(player.known.get(clue.t))}</td>
            ))}
          </tr>
        ))}
      </tbody>
      <tfoot>
        <tr>
          <th scope="row" colSpan={3}>
            {payoff === null ? "Clues so far" : `Clues before the payoff at t = ${payoff}`}
          </th>
          {players.map((player) => {
            const prepared = preparation(clues, player.known);
            return (
              <td key={player.id} className={prepared.tooFew ? styles.tooFew : undefined}>
                {prepared.text}
              </td>
            );
          })}
        </tr>
      </tfoot>
    </table>
  );
}
