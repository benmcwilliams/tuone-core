```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "EDL-Anlagenbau" or company = "EDL Anlagenbau")
sort location, dt_announce desc
```
