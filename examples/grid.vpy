# Ask user for some information, using sensible defaults.
eval "files=glob(input('Files [*.svg]? ') or '*.svg')"    # glob() creates a list of file based on a pattern
eval "cols=int(input('Number of columns [3]? ') or 3)"
eval "rows=ceil(len(files)/cols)"  # the number of rows depends on the number of files
eval "col_width=convert_length(input('Column width [10cm]? ') or '10cm')"  # convert_length() converts string like '3cm' to pixels
eval "row_height=convert_length(input('Row height [10cm]? ') or '10cm')"
eval "margin=convert_length(input('Margin [0.5cm]? ') or '0.5cm')"
eval "output_path=input('Output path [output.svg]? ') or 'output.svg'"

# Create a grid with provided parameters.
grid -o %col_width% %row_height% %cols% %rows%

    # Read the `_i`-th file. The last row may be incomplete so we use an empty path and `--no-fail`.
    read --no-fail "%files[_i] if _i < len(files) else ''%"

    # Layout the file in the cell.
    layout -m %margin% %col_width%x%row_height%
end

# wWrite the output file.
write "%output_path%"