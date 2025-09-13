# Copyright 2024 The android_world Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Runs a single task.

The minimal_run.py module is used to run a single task, it is a minimal version
of the run.py module. A task can be specified, otherwise a random task is
selected.
"""

import logging
import json
from datetime import datetime
import numpy as np
from PIL import Image as PILImage
import os
import shutil
import random
import sys
from collections.abc import Sequence
from typing import Optional, Type

from absl import app, flags
from android_world import registry
from android_world.env import env_launcher
from android_world.env.setup_device import setup
from android_world.task_evals import task_eval

# sys.path.append("/Users/vincent/Desktop/android_world/agents2_5")
from gui_agents.s2_5.agents.grounding import MobileACI
from gui_agents.s2_5.agents.agent_s import AgentS2_5


from dotenv import load_dotenv
load_dotenv()
# Set up logging


os.environ["GRPC_VERBOSITY"] = "ERROR"  # Only show errors
os.environ["GRPC_TRACE"] = "none"  # Disable tracing


def setup_logging(
    level: int = logging.INFO,
    log_format: Optional[str] = None,
    log_file: Optional[str] = None,
) -> None:
    """Sets up logging configuration for the entire application.
    
    Args:
        level: The logging level to use. Defaults to logging.INFO.
        log_format: Custom log format string. If None, uses default format.
        log_file: Optional file path to write logs to.
    """
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Create logger
    root_logger = logging.getLogger("android_world")
    root_logger.setLevel(level)

    # Remove any existing handlers
    root_logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(log_format)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(log_format)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Prevent propagation to root logger
    root_logger.propagate = False 


setup_logging(level=logging.INFO)
logger = logging.getLogger("android_world.run")

def _find_adb_directory() -> str:
    """Returns the directory where adb is located."""
    potential_paths = [
        os.path.expanduser("~/Library/Android/sdk/platform-tools/adb"),
        os.path.expanduser("~/Android/Sdk/platform-tools/adb"),
    ]
    for path in potential_paths:
        if os.path.isfile(path):
            return path
    raise EnvironmentError(
        "adb not found in the common Android SDK paths. Please install Android"
        " SDK and ensure adb is in one of the expected directories. If it's"
        " already installed, point to the installed location."
    )


_ADB_PATH = flags.DEFINE_string(
    "adb_path",
    _find_adb_directory(),
    "Path to adb. Set if not installed through SDK.",
)
_EMULATOR_SETUP = flags.DEFINE_boolean(
    "perform_emulator_setup",
    False,
    "Whether to perform emulator setup. This must be done once and only once"
    " before running Android World. After an emulator is setup, this flag"
    " should always be False.",
)
_DEVICE_CONSOLE_PORT = flags.DEFINE_integer(
    "console_port",
    5554,
    "The console port of the running Android device. This can usually be"
    " retrieved by looking at the output of `adb devices`. In general, the"
    " first connected device is port 5554, the second is 5556, and"
    " so on.",
)

_TASK = flags.DEFINE_string(
    "task",
    "ContactsAddContact",
    "A specific task to run.",
)


def _main() -> None:
    """Runs a single task."""
    env = env_launcher.load_and_setup_env(
        console_port=_DEVICE_CONSOLE_PORT.value,
        emulator_setup=_EMULATOR_SETUP.value,
        adb_path=_ADB_PATH.value,
    )
    env.reset(go_home=True)
    setup.reset_apps(env)
    task_registry = registry.TaskRegistry()
    aw_registry = task_registry.get_registry(task_registry.ANDROID_WORLD_FAMILY)
    if _TASK.value:
        if _TASK.value not in aw_registry:
            raise ValueError("Task {} not found in registry.".format(_TASK.value))
        task_type: Type[task_eval.TaskEval] = aw_registry[_TASK.value]
    else:
        task_type: Type[task_eval.TaskEval] = random.choice(list(aw_registry.values()))
    params = task_type.generate_random_params()
    task = task_type(params)
    task.initialize_task(env)

    engine_params = {"model": "gpt-5-2025-08-07", "engine_type": "openai"}
    engine_params_for_grounding = {
        "engine_type": "parasail",
        "model": "simular-ui-tars-1p5-7b",
        "base_url": os.getenv("PARASAIL_ENDPOINT_URL"),
        "api_key": os.getenv("PARASAIL_API_KEY"),
        "grounding_width": 1920,
        "grounding_height": 1080,
    }

    grounding_agent = MobileACI(
        engine_params_for_generation=engine_params,
        engine_params_for_grounding=engine_params_for_grounding,
        width=1080,
        height=2400,
    )

    agent = AgentS2_5(
        worker_engine_params=engine_params,
        grounding_agent=grounding_agent,
        platform="android",
        max_trajectory_length=8,
        enable_reflection=True,
    )


    print("Goal: " + str(task.goal))
    is_done = False
    print(task)
    print(task.complexity)
    step_summaries = []
    # Prepare results directory early so we can save per-step artifacts
    task_name = _TASK.value or task.__class__.__name__
    results_dir = os.path.join("results", str(task_name))
    # If the folder exists but no prior result.txt, clear it to start fresh
    try:
        if os.path.isdir(results_dir) and not os.path.isfile(os.path.join(results_dir, "result.txt")):
            shutil.rmtree(results_dir)
    except Exception as e:
        print(f"Could not clean previous results for {task_name}: {e}")
    os.makedirs(results_dir, exist_ok=True)
    traj_path = os.path.join(results_dir, "traj.jsonl")
    # Save initial screenshot once
    try:
        initial_state = env.get_state(wait_to_stabilize=True)
        init_arr = getattr(initial_state, "pixels", None)
        if isinstance(init_arr, np.ndarray):
            a = init_arr
            if a.dtype != np.uint8:
                if np.issubdtype(a.dtype, np.floating):
                    max_val = float(np.nanmax(a)) if a.size else 1.0
                    if max_val <= 1.0:
                        a = np.clip(a, 0.0, 1.0) * 255.0
                    else:
                        a = np.clip(a, 0.0, 255.0)
                    a = a.round().astype(np.uint8)
                else:
                    a = np.clip(a, 0, 255).astype(np.uint8)
            if not a.flags["C_CONTIGUOUS"]:
                a = np.ascontiguousarray(a)
            if a.ndim == 3 and a.shape[0] in (1, 3, 4) and a.shape[-1] not in (1, 3, 4):
                a = np.transpose(a, (1, 2, 0))
            mode = None
            if a.ndim == 2:
                mode = "L"
            elif a.ndim == 3:
                c = a.shape[2]
                if c == 1:
                    a = a[:, :, 0]
                    mode = "L"
                elif c == 3:
                    mode = "RGB"
                elif c == 4:
                    mode = "RGBA"
                else:
                    a = a[:, :, :3]
                    mode = "RGB"
            PILImage.fromarray(a, mode=mode).save(os.path.join(results_dir, "step_0.png"))
            try:
                with open(traj_path, "a") as f:
                    json.dump({
                        "step": 0,
                        "type": "observation",
                        "image": "step_0.png",
                        "timestamp": datetime.now().isoformat(timespec="seconds"),
                        "goal": str(task.goal),
                        "task_name": task_name,
                    }, f)
                    f.write("\n")
            except Exception as e:
                print(f"Could not append to traj.jsonl (initial): {e}")
    except Exception as e:
        print(f"Could not save initial screenshot: {e}")
    step_idx = 1
    for _ in range(int(task.complexity * 10)):
        response, info = agent.step(env, task.goal)
        try:
            step_summaries.append(str(response.data.get("summary", "")))
        except Exception:
            pass
        # Save per-step screenshots if available
        try:
            def _to_uint8_image(arr):
                if not isinstance(arr, np.ndarray):
                    return None
                a = arr
                if a.dtype != np.uint8:
                    if np.issubdtype(a.dtype, np.floating):
                        max_val = float(np.nanmax(a)) if a.size else 1.0
                        if max_val <= 1.0:
                            a = np.clip(a, 0.0, 1.0) * 255.0
                        else:
                            a = np.clip(a, 0.0, 255.0)
                        a = a.round().astype(np.uint8)
                    else:
                        a = np.clip(a, 0, 255).astype(np.uint8)
                if not a.flags["C_CONTIGUOUS"]:
                    a = np.ascontiguousarray(a)
                # channel-first to channel-last
                if a.ndim == 3 and a.shape[0] in (1, 3, 4) and a.shape[-1] not in (1, 3, 4):
                    a = np.transpose(a, (1, 2, 0))
                mode = None
                if a.ndim == 2:
                    mode = "L"
                elif a.ndim == 3:
                    c = a.shape[2]
                    if c == 1:
                        a = a[:, :, 0]
                        mode = "L"
                    elif c == 3:
                        mode = "RGB"
                    elif c == 4:
                        mode = "RGBA"
                    else:
                        a = a[:, :, :3]
                        mode = "RGB"
                return PILImage.fromarray(a, mode=mode) if mode else PILImage.fromarray(a)

            after = response.data.get("after_screenshot")
            if after is not None:
                img = _to_uint8_image(after)
                if img is not None:
                    img.save(os.path.join(results_dir, f"step_{step_idx}.png"))
            # Append trajectory entry
            try:
                with open(traj_path, "a") as f:
                    json.dump({
                        "step": step_idx,
                        "type": "step",
                        "image": f"step_{step_idx}.png",
                        "summary": response.data.get("summary"),
                        "action": response.data.get("action_output"),
                        "plan": info.get("plan"),
                        "plan_code": info.get("plan_code"),
                        "exec_code": info.get("exec_code"),
                        "reflection": info.get("reflection"),
                        "timestamp": datetime.now().isoformat(timespec="seconds"),
                    }, f)
                    f.write("\n")
            except Exception as e:
                print(f"Could not append to traj.jsonl (step {step_idx}): {e}")
        except Exception as e:
            print(f"Could not save step {step_idx} screenshots: {e}")
        if response.done:
            is_done = True
            break
        step_idx += 1
    agent_successful = is_done and task.is_successful(env) == 1
    print(
        f'{"Task Successful ✅" if agent_successful else "Task Failed ❌"};'
        f" {task.goal}"
    )
    # ----- Persist minimal results -----
    try:
        results_payload = {
            "task_name": task_name,
            "goal": str(task.goal),
            "success": bool(agent_successful),
            "steps": int(getattr(agent, "step_count", 0)),
            "turns": int(getattr(agent, "turn_count", 0)),
            "step_summaries": step_summaries,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
        with open(os.path.join(results_dir, "run.json"), "w") as f:
            json.dump(results_payload, f, indent=2)
        print(f"Saved results to {os.path.join(results_dir, 'run.json')}")
        # Write score to result.txt (1 on success, 0 on failure)
        score = 1 if agent_successful else 0
        with open(os.path.join(results_dir, "result.txt"), "w") as f:
            f.write(str(score))
    except Exception as e:
        print(f"Could not save results: {e}")
    env.close()


def main(argv: Sequence[str]) -> None:
    del argv
    _main()


if __name__ == "__main__":
    app.run(main)
