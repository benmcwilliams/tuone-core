```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Advanced-Electric-Machines-Research" or company = "Advanced Electric Machines Research")
sort location, dt_announce desc
```
