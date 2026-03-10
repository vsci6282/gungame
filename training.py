from env import GunEnv
import time
import os
import matplotlib.pyplot as plt
import pdb
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.env_checker import check_env

#Train the agent

currentModelID = 5


def learning_rate_schedule(progress_remaining):
    start_rate = 0.0001
    return (start_rate * progress_remaining) - 0.0001 #linearly decreasing

PPO_model_args = {
    "learning_rate": learning_rate_schedule, #decreasing learning rate #0.0003 #can be set to constant
    "gamma": 0.99, #0.99, discount factor for future rewards, between 0 (only immediate reward matters) and 1 (future reward equivalent to immediate),
    "verbose": 0, #change to 1 to get more info on training steps
    "ent_coef": 0.02, #0, entropy coefficient, to encourage exploration
    "clip_range": 0.2 #0.2, very roughly: probability of an action can not change by more than a factor 1+clip_range
}

log_dir = "log"
os.makedirs(log_dir, exist_ok=True)
env = GunEnv(False, False, None, False)
check_env(env, warn=True)
eval_callback = EvalCallback(env, best_model_save_path='./log/',
                             log_path='./log/', eval_freq=5000,
                             deterministic=False, render=False)
try:
    env.addModeltoList(PPO.load(f"model/model{currentModelID-1}.zip", env=env))
except FileNotFoundError:
    env.addModeltoList(PPO("MultiInputPolicy", env, **PPO_model_args))
env.currentModelID = currentModelID
starttime = time.time()
model = PPO('MultiInputPolicy', env, **PPO_model_args)
model.ID = currentModelID
#Load previous best model parameters, we start from that
if os.path.exists("log/best_model.zip"):
    model.set_parameters("log/best_model.zip")
for i in range(0, 10):
    print(f'started training model v{currentModelID}')
    model.learn(total_timesteps=750_000, progress_bar=True)
    model.save(f"model/model{currentModelID}")
    env.addModeltoList(PPO.load(f"model/model{currentModelID}.zip", env=env))
    currentModelID += 1
    env.currentModelID = currentModelID
    env.maxTrainingSteps += 100
dt = time.time()-starttime
print("Calculation took %g hr %g min %g s"%(dt//3600, (dt//60)%60, dt%60) )
