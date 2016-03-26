from fruitpile import Fruitpile
fp = Fruitpile()
fp.init()
fp.open()
fs = fp.add_new_fileset(name="test-1")
bf = fp.add_file(source_file="requirements.txt", fileset_id=fs.id, name="r.txt", path="deploy", version="1", revision="a7d6b66", primary=True, source="buildbot")
bfs = fp.list_files()
print bfs
