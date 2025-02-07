```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "China-Triumph-International-Engineering-Company" or company = "China Triumph International Engineering Company")
sort location, dt_announce desc
```
