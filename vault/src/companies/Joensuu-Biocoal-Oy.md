```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Joensuu-Biocoal-Oy" or company = "Joensuu Biocoal Oy")
sort location, dt_announce desc
```
