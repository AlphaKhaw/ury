import { call, db, auth } from './frappe-sdk';

type LoggedUserResponse = string | null;

interface UserDoc {
  name: string;
  full_name: string;
  roles: Array<{
    name: string;
    role: string;
    parent: string;
  }>;
}

export const getLoggedUser = async (): Promise<LoggedUserResponse> => {
  try {
    const response = await auth.getLoggedInUser();
    return response as LoggedUserResponse;
  } catch (error) {
    console.error('Error getting logged user:', error);
    return null;
  }
};

export const getUserRoles = async (email: string): Promise<{ roles: string[]; full_name: string }> => {
  try {
    // Get user roles using the proper API
    const rolesResponse = await call.post('frappe.core.doctype.user.user.get_all_roles', { user: email });
    
    // Get user details for full_name
    const userDoc = await db.getDoc<UserDoc>('User', email);
    
    return {
      roles: rolesResponse.message || [],
      full_name: userDoc.full_name || ''
    };
  } catch (error) {
    console.error('Error getting user details:', error);
    return { roles: [], full_name: '' };
  }
};

export const logout = async () => {
  try {
    return auth.logout();
  }catch(e){
    console.error('Error logging out:', e);
    return false;
  }
}