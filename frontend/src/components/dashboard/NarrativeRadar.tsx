import Section from "../layout/Section";
import NarrativeCard from "./NarrativeCard";
import type { RadarTopic } from "../../types/rhetoriq";

type NarrativeRadarProps = {
  topics: RadarTopic[];
};

export default function NarrativeRadar({ topics }: NarrativeRadarProps) {
  return (
    <Section
      eyebrow="Live Narrative Radar"
      title="What is breaking into the conversation right now?"
      description="A seeded radar pass keeps the homepage dependable while we wire in live narrative detection. Each card is framed around spread signals, source mix, and investigation readiness."
      className="pt-6"
    >
      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {topics.map((topic) => (
          <NarrativeCard key={topic.id} topic={topic} />
        ))}
      </div>
    </Section>
  );
}
