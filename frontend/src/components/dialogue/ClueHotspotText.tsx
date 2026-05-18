import type { SceneHighlight } from '../../types/game';

type ClueHotspotTextProps = {
  text: string;
  sceneId: string;
  highlights: SceneHighlight[];
  busy: boolean;
  onInspect: (sceneId: string, hotspotId: string, clueId?: string | null) => void;
};

export function ClueHotspotText({ text, sceneId, highlights, busy, onInspect }: ClueHotspotTextProps) {
  const nodes: Array<string | SceneHighlight> = [];
  let remaining = text;

  highlights.forEach((highlight) => {
    const index = remaining.indexOf(highlight.text);
    if (index < 0) {
      return;
    }
    if (index > 0) {
      nodes.push(remaining.slice(0, index));
    }
    nodes.push(highlight);
    remaining = remaining.slice(index + highlight.text.length);
  });

  if (remaining) {
    nodes.push(remaining);
  }

  if (!nodes.length) {
    return <>{text}</>;
  }

  return (
    <>
      {nodes.map((node, index) => {
        if (typeof node === 'string') {
          return <span key={`${node}-${index}`}>{node}</span>;
        }
        return (
          <button
            key={`${node.hotspot_id}-${index}`}
            type="button"
            className="clue-hotspot-text"
            onClick={() => onInspect(sceneId, node.hotspot_id, node.clue_id)}
            disabled={busy}
          >
            {node.text}
          </button>
        );
      })}
    </>
  );
}
