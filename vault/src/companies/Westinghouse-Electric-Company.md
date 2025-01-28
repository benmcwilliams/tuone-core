```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Westinghouse-Electric-Company" or company = "Westinghouse Electric Company")
sort location, dt_announce desc
```
