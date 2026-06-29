import datetime

from wellness_tracker.agents.whoop_brief import WhoopBriefAgent
from wellness_tracker.models.envelope import DailyEnvelope, WhoopDayContext
from wellness_tracker.models.outputs import WhoopBriefOutput
from wellness_tracker.storage.diary import load_envelope, save_envelope
from wellness_tracker.storage.objectives import load_current_objectives


class Orchestrator:
    def process(self, input_type: str, raw_text: str) -> dict:
        objectives, version = load_current_objectives()
        envelope = self._load_or_create_envelope(objectives.week_starting, version)

        if input_type == "whoop_brief":
            return self._handle_whoop_brief(raw_text, envelope)

        raise NotImplementedError(f"Input type {input_type} not yet implemented")

    def _handle_whoop_brief(self, raw_text: str, envelope: DailyEnvelope) -> dict:
        agent = WhoopBriefAgent()
        output: WhoopBriefOutput = agent.run({"raw_text": raw_text})

        if output.status == "success" and output.strain_target is not None:
            envelope.whoop = WhoopDayContext(strain_target=output.strain_target)

        path = save_envelope(envelope)
        return {"status": output.status, "output": output, "path": path}

    def _load_or_create_envelope(
        self, week_starting: str, objectives_version: str
    ) -> DailyEnvelope:
        date = datetime.date.today().isoformat()
        try:
            return load_envelope(date)
        except FileNotFoundError:
            return DailyEnvelope(
                date=date,
                week_starting=week_starting,
                objectives_version=objectives_version,
            )
