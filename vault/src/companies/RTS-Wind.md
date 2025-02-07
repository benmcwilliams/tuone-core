```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "RTS-Wind" or company = "RTS Wind")
sort location, dt_announce desc
```
