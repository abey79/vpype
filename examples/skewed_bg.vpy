# example of command file
begin
  grid -o 1cm 1cm 20 20
  random -n 10 --area 0.3cm 0.3cm
  translate 0.35cm 0.35cm
  circle 0.5cm 0.5cm 0.5cm
  frame
end
skew 15 15
rotate 45
crop 5cm 5cm 10cm 10cm
frame
