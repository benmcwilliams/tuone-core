```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Forth-Ports" or company = "Forth Ports")
sort location, dt_announce desc
```
