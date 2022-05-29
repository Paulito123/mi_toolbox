import os
import shutil
import wget
import zipfile


print(f"...AND OFF WE GO !")

workdir = "/home/user/workdirectory/"
configfile = "config.csv"
template_toml = "0L.template.toml"
final_toml = "0L.toml"
template_env = "template.env"
final_env = ".env"
env_dir = "envs"
configdir = ".0L"
repo_dir = "0l-operations"
vdfdir = "vdf_proofs"
shelldir = "shell"
statement = "No statement"
ip = "1.2.3.4"
vfn_ip = "0.0.0.0"
upstream = "http://63.229.234.76:8080/"
proof_base_url = 'https://0l.interblockcha.in/api/proofs/'
template_dc = "docker-compose.template.yml"
final_dc = "docker-compose.yml"

template_tower = '  tower<#1#>:\n' \
                 '    image: "${OL_IMAGE}"\n' \
                 '    container_name: "0l-tower<#1#>"\n' \
                 '    restart: "on-failure"\n' \
                 '    network_mode: host\n' \
                 '    pid: host\n' \
                 '    depends_on:\n' \
                 '      - node\n' \
                 '    volumes:\n' \
                 '      - "t<#1#>_data:/root/.0L"\n' \
                 '    entrypoint: "tower ${OL_TOWER_OPERATOR} ${OL_TOWER_USE_FIRST_UPSTREAM} ${OL_TOWER_VERBOSE} start"\n' \
                 '    ulimits:\n' \
                 '      nproc: 100000\n' \
                 '      nofile: 100000\n' \
                 '    environment:\n' \
                 '      NODE_ENV: "prod"\n' \
                 '      TEST: "${OL_TOWER_TEST-n}"\n' \
                 '    env_file:\n' \
                 '      - "./envs/t<#1#>/.env"'

template_volume = '  t<#1#>_data:\n' \
                  '    driver: local\n' \
                  '    driver_opts:\n' \
                  '      type: none\n' \
                  '      o: bind\n' \
                  '      device: "${OL_DATA_DIR}t<#1#>/"'

# read config file
print("...reading config file")
configfile_path = f'{workdir}{configfile}'
cfile = open(configfile_path, 'r')
lines = cfile.readlines()

# make root config directory
print("...creating output dirs")
configdir_path = f"{workdir}{configdir}"
os.mkdir(configdir_path)
repo_dir_path = f"{workdir}{repo_dir}"
os.mkdir(repo_dir_path)
env_dir_path = f"{repo_dir_path}/{env_dir}"
os.mkdir(env_dir_path)

# make shell dir
shelldir_path = f"{configdir_path}/{shelldir}"
os.mkdir(shelldir_path)
vdfdir_path = f"{shelldir_path}/{vdfdir}"
os.mkdir(vdfdir_path)

# copy docker-compose template
print(f"...create docker compose file")
template_dc_path = f"{workdir}{template_dc}"
final_dc_path = f"{repo_dir_path}/{final_dc}"
shutil.copyfile(template_dc_path, final_dc_path)

# Strips the newline character
print(f"...iterating config file")
counter = 1
for line in lines:
    row = line.split(',')
    accnr = row[0]
    addr = row[1]
    authkey = row[2]
    mnem = row[3].rstrip('\r\n')
    print(f"...creating files and directories for account ({accnr}) -> {addr}")

    # make tower dir by account
    final_tower_dir = f"{configdir_path}/t{accnr}"
    os.mkdir(final_tower_dir)

    # make env dir by account
    final_env_dir = f"{env_dir_path}/t{accnr}"
    os.mkdir(final_env_dir)

    # make vdf_proofs dir
    final_vdf_path = f"{final_tower_dir}/{vdfdir}"
    os.mkdir(final_vdf_path)

    # get the proofs
    print(f"...downloading proofs")
    site_url = f'{proof_base_url}{addr}'
    try:
        path_to_zip_file = wget.download(url=site_url, out=final_vdf_path)
        # unzip the proofs
        print(f"...unzipping proofs for {accnr}")
        with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
            zip_ref.extractall(final_vdf_path)
        # remove the zip file
        os.remove(path_to_zip_file)
    except Exception as e:
        print(f"{e}")

    # update docker-compose file
    print(f"...updating docker-compose file")
    tower_expr = f"<#{counter}#>"
    vol_expr = f"<#v{counter}#>"
    with open(final_dc_path, 'r') as file:
        dcfile = file.read()

    tower_output = template_tower.replace('<#1#>', accnr)
    dcfile = dcfile.replace(tower_expr, tower_output)
    volume_output = template_volume.replace('<#1#>', accnr)
    dcfile = dcfile.replace(vol_expr, volume_output)

    # Write the file out again
    with open(final_dc_path, 'w') as file:
        file.write(dcfile)

    # copy toml template
    print(f"...creating toml file")
    template_toml_path = f"{workdir}{template_toml}"
    final_toml_path = f"{final_tower_dir}/{final_toml}"
    shutil.copyfile(template_toml_path, final_toml_path)

    # Read in the file
    with open(final_toml_path, 'r') as file:
        tomlfile = file.read()

    # Replace the target string
    tomlfile = tomlfile.replace('<#1#>', addr)
    tomlfile = tomlfile.replace('<#2#>', authkey)
    tomlfile = tomlfile.replace('<#3#>', statement)
    tomlfile = tomlfile.replace('<#4#>', ip)
    tomlfile = tomlfile.replace('<#5#>', vfn_ip)
    tomlfile = tomlfile.replace('<#6#>', upstream)

    # Write the file out again
    with open(final_toml_path, 'w') as file:
        file.write(tomlfile)

    # make .env
    print(f"...creating .env file")
    template_env_path = f"{workdir}{template_env}"
    final_env_path = f"{final_env_dir}/{final_env}"
    shutil.copyfile(template_env_path, final_env_path)

    # Read in the file
    with open(final_env_path, 'r') as file:
        envfile_data = file.read()

    # Replace the target string
    envfile_data = envfile_data.replace('<#1#>', mnem)

    # Write the file out again
    with open(final_env_path, 'w') as file:
        file.write(envfile_data)

    # increase counter
    counter = counter + 1

    print(f"...acount {accnr} done!")

print("BAM!!! All done!")