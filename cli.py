import app
import sys

gentle = app.GentleFA()
with open(sys.argv[1]) as i_file, open(sys.argv[2], 'w') as o_file:
    o_file.write(str(gentle.annotate(i_file.read())))