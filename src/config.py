from environs import Env

env = Env()
env.read_env()

API_PORT = env.str("API_PORT")
SELENOID_COMMAND_EXECUTOR = env.str("SELENOID_COMMAND_EXECUTOR")
