import json
from candidate_transformer.cli.context import PipelineContext
from candidate_transformer.cli.commands import CommandDispatcher, workspace_manager

context = PipelineContext(workspace_name="test_ws")
dispatcher = CommandDispatcher(context)

dispatcher.dispatch("load recruiter_csv sample_data/recruiter.csv")
dispatcher.dispatch("load ats_json sample_data/ats.json")
dispatcher.dispatch("load resume_text sample_data/resume.txt")
dispatcher.dispatch("build")
