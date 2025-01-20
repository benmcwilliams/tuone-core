```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and company = "Fortum Power and Heat Oy"
sort location, dt_announce desc
```
