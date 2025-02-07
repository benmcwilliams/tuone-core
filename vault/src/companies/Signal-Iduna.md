```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Signal-Iduna" or company = "Signal Iduna")
sort location, dt_announce desc
```
