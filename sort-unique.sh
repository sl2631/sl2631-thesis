
path="$1"
path_old="$path.old"
mv "$path" "$path_old"
sort "$path_old" | uniq > "$path"
