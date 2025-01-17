```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "B&K Solare Zukunft"
sort location, dt_announce desc
```
