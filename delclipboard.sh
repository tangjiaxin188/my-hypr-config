for i in $(cliphist list | awk '{print $2}' | cut -c 1| uniq );do cliphist delete-query "$i"; done
