```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Aspira-Aerial-Applications" or company = "Aspira Aerial Applications")
sort location, dt_announce desc
```
