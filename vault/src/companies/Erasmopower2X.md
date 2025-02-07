```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Erasmopower2X" or company = "Erasmopower2X")
sort location, dt_announce desc
```
