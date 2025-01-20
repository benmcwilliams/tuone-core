```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and company = "EU renewable energy financing mechanism"
sort location, dt_announce desc
```
