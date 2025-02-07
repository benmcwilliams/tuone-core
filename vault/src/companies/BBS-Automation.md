```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "BBS-Automation" or company = "BBS Automation")
sort location, dt_announce desc
```
