```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Institute-for-Solar-Energy-Research-Hamelin-(ISFH)" or company = "Institute for Solar Energy Research Hamelin (ISFH)")
sort location, dt_announce desc
```
