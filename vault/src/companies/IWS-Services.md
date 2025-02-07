```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "IWS-Services" or company = "IWS Services")
sort location, dt_announce desc
```
