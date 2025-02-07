```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Deutsche-Erdwärme" or company = "Deutsche Erdwärme")
sort location, dt_announce desc
```
