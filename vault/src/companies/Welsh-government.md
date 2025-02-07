```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Welsh-government" or company = "Welsh government")
sort location, dt_announce desc
```
