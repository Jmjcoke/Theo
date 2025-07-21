import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { CheckCircle, XCircle } from "lucide-react";

const UserManagementPage = () => {
  const pendingUsers = [
    {
      email: "scholar1@seminary.edu",
      registrationDate: "2024-01-15",
      institution: "Westminster Seminary"
    },
    {
      email: "researcher@theology.org",
      registrationDate: "2024-01-14",
      institution: "Dallas Theological Seminary"
    },
    {
      email: "student@divinity.edu",
      registrationDate: "2024-01-13",
      institution: "Yale Divinity School"
    }
  ];

  const handleApprove = (email: string) => {
    // TODO: Implement approval logic
    console.log("Approving user:", email);
  };

  const handleDeny = (email: string) => {
    // TODO: Implement denial logic
    console.log("Denying user:", email);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <span>Pending User Approvals</span>
            <span className="bg-warning/10 text-warning px-2 py-1 rounded-full text-xs font-medium">
              {pendingUsers.length} pending
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Email</TableHead>
                <TableHead>Institution</TableHead>
                <TableHead>Registration Date</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {pendingUsers.map((user, index) => (
                <TableRow key={index}>
                  <TableCell className="font-medium">
                    {user.email}
                  </TableCell>
                  <TableCell>{user.institution}</TableCell>
                  <TableCell>{user.registrationDate}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end space-x-2">
                      <Button
                        size="sm"
                        onClick={() => handleApprove(user.email)}
                        className="bg-success hover:bg-success/90"
                      >
                        <CheckCircle className="h-4 w-4 mr-1" />
                        Approve
                      </Button>
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => handleDeny(user.email)}
                      >
                        <XCircle className="h-4 w-4 mr-1" />
                        Deny
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export default UserManagementPage;