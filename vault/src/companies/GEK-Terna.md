```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "GEK-Terna" or company = "GEK Terna")
sort location, dt_announce desc
```
