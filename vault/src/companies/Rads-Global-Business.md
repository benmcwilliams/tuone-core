```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Rads-Global-Business" or company = "Rads Global Business")
sort location, dt_announce desc
```
