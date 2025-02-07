```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Bluefield-Renewable-Developments" or company = "Bluefield Renewable Developments")
sort location, dt_announce desc
```
