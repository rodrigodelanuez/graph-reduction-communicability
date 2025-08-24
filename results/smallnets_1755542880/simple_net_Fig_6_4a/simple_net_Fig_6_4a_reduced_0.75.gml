graph [
  node [
    id 0
    label "('0','7')"
  ]
  node [
    id 1
    label "(('1', '2'),'8')"
  ]
  node [
    id 2
    label "('11',((('10', (('3', '4'), '9')), '5'), '6'))"
  ]
  edge [
    source 0
    target 1
  ]
  edge [
    source 0
    target 2
  ]
  edge [
    source 1
    target 2
  ]
]
