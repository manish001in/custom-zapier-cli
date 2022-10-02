import os, sys
from subprocess import Popen, PIPE, STDOUT

if __name__ == "__main__":
    # Setup environ
    sys.path.append(os.getcwd())
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zapier.settings")

    # Setup django
    import django

    django.setup()
    from django.conf import settings

    os.system("mkdir -p " + settings.DOWNLOAD_DIR)

    from zapier import command_line

    input_string = command_line.start_app()
    ctx = command_line.Context()

    while True:
        input_command = (raw_input(input_string + " ")).strip()
        if input_command == "exit":
            break
        input_string = "\n" + command_line.parse_command(input_command, ctx)
