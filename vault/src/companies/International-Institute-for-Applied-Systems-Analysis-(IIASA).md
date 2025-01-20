```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and company = "International Institute for Applied Systems Analysis (IIASA)"
sort location, dt_announce desc
```
