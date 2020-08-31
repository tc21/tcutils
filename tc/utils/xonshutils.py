import subprocess as __subprocess


def _detached_helper(args):
    """ right now this doesn't actually detach the process from xonsh """
    p = __subprocess.Popen(args,
                           stdin=__subprocess.PIPE,
                           stdout=__subprocess.PIPE,
                           stderr=__subprocess.PIPE)
    p.stdin.close()
    p.stdout.close()
    p.stderr.close()
