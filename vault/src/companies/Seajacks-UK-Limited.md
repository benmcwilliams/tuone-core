```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and company = "Seajacks UK Limited"
sort location, dt_announce desc
```
